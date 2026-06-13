import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { environment } from '../../environments/environment';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class TournamentService {
  private supabase: SupabaseClient;
  private backendUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient) {
    // Initialize direct Supabase connection
    this.supabase = createClient(environment.supabaseUrl, environment.supabaseKey);
  }

  /**
   * Send match teams to FastAPI Python microservice to get the ML prediction
   */
  getPrediction(homeTeam: string, awayTeam: string): Observable<{ winner: string }> {
    return this.http.post<{ winner: string }>(`${this.backendUrl}/predict`, {
      home_team: homeTeam,
      away_team: awayTeam
    });
  }

  /**
   * Save completed tournament tree structure directly to Supabase
   */
  async saveBracket(username: string, bracketTree: any): Promise<any> {
    const { data, error } = await this.supabase
      .from('predictions')
      .insert([
        { username: username, tournament_tree: bracketTree }
      ]);

    if (error) throw error;
    return data;
  }
}